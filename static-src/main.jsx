
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
        return <div key={integ.key}></div>
    },
    render() {
        return (
            <div>
                {this.state.integrations.map(this.renderIntegration)}
                <Platforms />
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
        this.sock = new WebSocket('ws://l:7999/ws/');
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
        this.setState({input: null, messages: this.state.messages})
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
                <Integrations />
            </div>
        )
    }
})

$(function() {
    var app = $('#app')
    if (app.length) {
        ReactDOM.render(<Conversation />, app[0])
    }
})
