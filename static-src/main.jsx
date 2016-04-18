
const Integrations = React.createClass({
    getInitialState() {
        return {
            integrations: []
        }
    },
    componentDidMount() {
        $.ajax('/api/v1/integrations/', {success: this.loadIntegrations})
    },
    loadIntegrations(data) {
        this.setState({integrations: data.integrations})
    },
    renderIntegration(integ) {
        return <div key={integ.key}>{JSON.stringify(integ)}</div>
    },
    render() {
        return (
            <div>
                {this.state.integrations.map(this.renderIntegration)}
            </div>
        )
    }
})


const Platforms = React.createClass({
    getInitialState() {
        return {
            platforms: [],
            platform: null,
        }
    },
    componentDidMount() {
        $.ajax('/api/v1/platforms/', {success: this.loadPlatforms})
    },
    loadPlatforms(data) {
        this.setState({platforms: data.platforms})
    },
    newPlatform(e) {
        e.preventDefault()
        let platform = this.state.platform
        let name = platform.name
        let authData = {}
        platform.fields.map((field) => {
            authData[field.name] = this.refs["form-" + field.name].value
        })
        let data = {
            platform: name,
            authData: JSON.stringify(authData),
        }
        $.ajax("/api/v1/integrations/", {
            method: "post",
            data: data, 
        })
    },
    renderPlatform(plat) {
        return (
            <div key={plat.name}>
                <img src={"/static/images/logos/" + plat.logo} />
                <div><b>Name: </b> {plat.name}</div>
                <button onClick={() => {this.setState({platform: plat})}}>New</button>
            </div>
        )
    },
    renderFormField(field) {
        return (
            <div key={field.name}>
                <label htmlFor={field.name}>{field.label}</label>
                <input ref={"form-"+field.name}type={field.type} name={this.name} value={undefined} />
            </div>
        )
    },
    render() {
        let form = null
        if (this.state.platform) {
            form = (
                <form onSubmit={this.newPlatform}>
                    {this.state.platform.fields.map(this.renderFormField)}
                    <button>Submit</button>
                </form>
            )
        }
        return (
            <div>
                {this.state.platforms.map(this.renderPlatform)}
                {form}
            </div>
        )
    },
})

const Panel = React.createClass({
    render() {
        return (
            <div className="panel panel-default">
                <div className="panel-heading">
                    <div className="panel-title">
                        {this.props.title}
                    </div>
                </div>
                <div className="panel-body">
                    {this.props.children}
                </div>
            </div> 
        )
    },
})

const Conversation = React.createClass({
    sock: null,
    getInitialState() {
        return {
            messages: [],
            input: "",
            status:'dead',
        }
    },
    componentDidMount() {
        $.ajax('/api/v1/messages/', {success: this.loadMessages})
        this.sock = new WebSocket('ws://l:8081/ws/');
        this.sock.onmessage = this.onMessage
        this.sock.onopen = this.onOpen
        this.sock.onclose = this.onClose
    },
    loadMessages(data) {
        this.setState({messages: data.messages})
    },
    onMessage(e) {
        let message = JSON.parse(e.data)
        let updated = false
        for(var i=0;i<this.state.messages.length;i++) {
            if (this.state.messages[i].token === message.token) {
                this.state.messages[i] = message
                updated = true
            }
        }
        if (updated === false) {
            this.state.messages.push(message)
        }
        this.setState({messages: this.state.messages})
    },
    onOpen(e) {
        this.setState({status: 'live'})
    },
    onClose(e) {
        this.setState({status: 'dead'})
    },
    renderMessage(message) {
        let className = null
        if (message.unconfirmed) {
            className = "unconfirmed"
        }
        return <p key={message.token} className={className}>{message.msg}</p>
    },
    inputChange() {
        this.setState({
            input: this.refs.inputInput.value
        })
    },
    inputSubmit(e) {
        e.preventDefault()
        let token = Math.random() + "-" + Date.now()
        let message = {
            msg: this.state.input,
            token: token,
        }
        this.sock.send(JSON.stringify(message))
        message.unconfirmed = true
        this.state.messages.push(message)
        this.setState({input: "", messages: this.state.messages})
    },
    render() {
        return (
            <div className="conversation">
                <div className="messages">
                    Messages
                    {this.state.messages.map(this.renderMessage)}
                </div>
                <div className="input">
                    {this.state.status}
                    <form ref="inputForm" onSubmit={this.inputSubmit}>
                        <input type="text" ref="inputInput" onChange={this.inputChange} value={this.state.input} />
                        <button type="submit">Submit</button>
                    </form>
                </div>
            </div>
        )
    }
})

const App = React.createClass({
    render() {
        return (
            <div>
                <Panel title="conversation">
                    <Conversation />
                </Panel>
                <Panel title="Integrations">
                    <Integrations />
                </Panel>
                <Panel title="Platforms">
                    <Platforms />
                </Panel>
            </div>
        )
    },
})

const LoadingButton = React.createClass({
    render() {
        let text = this.props.text
        if (this.props.loading === true) {
            text = "Loading..."
        }
        return (
            <button 
                className={this.props.className || "btn btn-info"}
                onClick={this.props.onClick}>
                {text}
            </button>
        )
    }
})

// Do not conflict with Shopify or ShopifyApp namespace
const ShopifyAppComponent = React.createClass({
    getInitialState() {
        let installStep = 1
        let installing = true

        if (window.shopifyUser.pageId) {
            installing = false
        }
        if (window.shopifyUser.facebookToken) {
            installStep = 2
        }

        return {
            pages: [],
            installStep: installStep,
            installing: installing,
            loading: false,
            error: null,
            shopifyUser: window.shopifyUser
        }
    },
    componentDidMount() {
    },
    getFacebookPages(token) {
        this.ajax({
            url: '/shopify/get-facebook-pages/',
            method: 'post',
            data: {
                facebookToken: token,
            },
            success: (data) => {
                this.setState({
                    pages: data.pages.data,
                    installStep: 2,
                })
                console.log(data)
            }
        })
    },
    facebookLogin(){
        FB.login((e) => {
            console.log(e)
            this.getFacebookPages(e.authResponse.accessToken)
        }, {scope: 'pages_messaging,manage_pages'})
    },
    renderOptionForPage(page) {
        return (
            <option 
            key={page.id} 
            data-id={page.id} 
            data-token={page.access_token}
            data-name={page.name}
            >{page.name}</option>
        )
    },
    ajax(object) {
        this.setState({
            error: null,
            loading: true,
        })
        if (!object.method) {
            object.method = "get"
        }
        $.ajax({
            url: object.url,
            data: object.data,
            method: object.method,
            success: (data) => {
                this.setState({loading: false})
                object.success(data)
            },
            error: (data) => {
                if (object.error) {
                    object.error()
                }
                this.setState({error: "There was an error performing this request!"})
            }
        })
    },
    changePage() {
        this.setState({
            installing: true,
            installStep: 1,
        })
    },
    contentFormSubmit(e) {
        e.preventDefault()
        this.state.shopifyUser.welcomeMessage = $(this.refs.welcomeMessage).val()
        this.setState({shopifyUser: this.state.shopifyUser})
        this.updateShopifyUser()
    },
    updateShopifyUser() {
        this.ajax({
            url: '/shopify/update-user/',
            method: "GET",
            data: this.state.shopifyUser,
            success: (data) => {
                this.setState({shopifyUser: data})
            },
        })
    },
    selectPage() {
        let selected = $(this.refs.pageSelect).find(':selected')

        let pageId = selected.data('id')
        let facebookPageToken = selected.data('token')
        let facebookPageName = selected.data('name')

        this.ajax({
            url: '/shopify/select-page/',
            method: 'POST',
            data: {
                pageId: pageId,
                facebookPageToken: facebookPageToken,
                facebookPageName: facebookPageName,
            },
            success: (data) => {
                this.state.shopifyUser.pageId = pageId
                this.state.shopifyUser.facebookPageToken = facebookPageToken
                this.state.shopifyUser.facebookPageName = facebookPageName
                this.setState({
                    installing: false,
                    shopifyUser: this.state.shopifyUser,
                })
            },
        })
    },
    getContent() {
        if (this.state.installing === true) {
            if (this.state.installStep === 1) {
                return (
                    <div>
                        <p>
                            Hello! Welcome to Fan. 
                        </p><p>
                            We're excited to get you started selling products
                            through facebook messenger. To get started, log into your facebook.
                        </p>
                        <LoadingButton 
                            text="Log In"
                            onClick={this.facebookLogin}
                            loading={this.state.loading}
                        />
                    </div>
                )
            } else if (this.state.installStep === 2) {
                window.setTimeout(() => {
                    $('select').focus()
                }, 100)
                return (<div>
                    <p>
                        Great! We've connected with your facebook. 
                    </p><p>
                        Select the facebook page you would like to sell
                        with from the dropdown below:
                    </p>
                    <p>
                        <select ref="pageSelect" className="form-control">
                            {this.state.pages.map(this.renderOptionForPage)}
                        </select>
                    </p>
                    <p>
                        <LoadingButton 
                            text="Use This Page"
                            onClick={this.selectPage}
                            loading={this.state.loading}
                        />
                    </p>
                </div>)
            }
        } else {
            let welcomeMessage = this.state.shopifyUser.welcomeMessage
            if (!welcomeMessage) {
                welcomeMessage = "Welcome! Type \"Go Shopping\" to shop right here on Messenger."
            }
            return (
                <div>
                    <h3 className="center">Fan Commerce</h3>
                    <div className="btn-group settings-dropdown">
                        <button type="button" className="btn btn-default dropdown-toggle" data-toggle="dropdown">
                            <i className="fa fa-cog"></i>
                        </button>
                        <ul className="dropdown-menu dropdown-menu-right">
                            <li><a href="#" onClick={this.changePage}>Change Facebook Page</a></li>
                            <li><a href="#" onClick={this.contactSupport}>Contact Support</a></li>
                        </ul>
                    </div>
                    <div className="btn-group menu-dropdown">
                        <button type="button" className="btn btn-default dropdown-toggle" data-toggle="dropdown">
                            <i className="fa fa-bars"></i>
                        </button>
                        <ul className="dropdown-menu dropdown-menu-left">
                            <li><a href="#content">Content</a></li>
                            <li><a href="#faq">FAQ</a></li>
                        </ul>
                    </div>
                    <p>
                        We're connected with your facebook page&nbsp; 
                        <b>{this.state.shopifyUser.facebookPageName}</b>.
                    </p>
                    <p>
                        Your customers can discover and purchase your products using facebook messenger.
                        Test it out by chatting with your store here: 
                    </p>
                    <div className="fb-messengermessageus" 
                        messenger_app_id={window.messengerAppId} 
                        page_id={this.state.shopifyUser.pageId} 
                        data-ref="nah" 
                        color="blue" 
                        size="small"></div>


                    <div className="content content-section">
                        <h3 className="center" id="content">
                            Content
                        </h3>
                        <form onSubmit={this.contentFormSubmit}>
                            <div className="form-group">
                                <label for="exampleInputEmail1">Welcome Message</label>
                                <textarea ref="welcomeMessage" type="email" className="form-control">{welcomeMessage}</textarea>
                                <p>
                                    Your welcome message is the first message your users recieve.
                                    Make sure it mentions that users have to type "Go Shopping"
                                    to start chatting with the bot.
                                </p>
                            </div>
                            <button className="btn btn-default btn-sm">
                                Save
                            </button>
                        </form>
                    </div>
                    <div className="faq content-section">
                        <h3 className="center" id="faq">
                            FAQ
                        </h3>
                        <p><b>Why is Fan Commerce Free?</b></p>
                        <p>
                            Fan commerce is currently in Beta. We want to get as many
                            messages as possible through the system early on so that
                            we can optimize and improve the bot logic. As soon as we're
                            out of Beta we'll likely move to a pay-per-use model with 
                            a useable free tier.
                        </p>
                        <p><b>How can I change the content of the bot responses?</b></p>
                        <p>
                            You can edit a custom welcome message. This will be the first
                            thing a customer is sent when they message your page. We don't
                            allow editing beyond that because we would like to continually
                            optimize and improve the presentation and text. If you have
                            any suggestions for how to improve our messaging please don't
                            hesistate to let us know.
                        </p>
                        <p><b>How many sales has Fan Commerce generated me?</b></p>
                        <p>
                            We add "FanCommerce" as the utm source for every visit to your
                            site. We're also working on conversion stats and displaying
                            bot data. Those should be added to the dashboard shortly.
                        </p>
                    </div>
                </div> 
            )
        }
        return ""
    },
    render() {
        let content = this.getContent()
        return (
            <div className="container">
                <div className="row">
                    <div className="col-md-6 col-md-offset-3">
                        <div className="white center">
                            <img className="logo" src="/static/images/fan2.png" />
                        </div>
                        <div className="panel panel-default shopify-app-panel">
                            <div className="panel-body center">
                                {content}
                            </div>
                        </div>
                        <br /> 
                        <div className="center">
                            <a 
                                href="https://www.iubenda.com/privacy-policy/7833616" 
                                target="_blank"
                                style={{color: 'white'}}
                            >privacy policy</a>
                        </div>
                    </div>
                </div>
            </div>
        )
    },
})

$(function() {
    var app = $('#app')
    if (app.length) {
        ReactDOM.render(<App />, app[0])
    }
    var app = $('#shopifyApp')
    if (app.length) {
        ReactDOM.render(<ShopifyAppComponent />, app[0])
    }
})
