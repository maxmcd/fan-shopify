

var newMessage = function(message) {
    return JSON.stringify({
        ts: Date.now(),
        msg: message,
    })
}

const Conversation = React.createClass({
    sock: null,
    getInitialState() {
        return {
            messages: [],
            input: null,
            status:'dead',
        }
    },
    componentDidMount() {
        this.sock = new WebSocket('ws://l:7999/ws/');
        this.sock.onmessage = this.onMessage
        this.sock.onopen = this.onOpen
        this.sock.onclose = this.onClose
    },
    onMessage(e) {
        this.state.messages.push(JSON.parse(e.data))
        this.setState({messages: this.state.messages})
    },
    onOpen(e) {
        this.setState({status: 'live'})
    },
    onClose(e) {
        this.setState({status: 'dead'})
    },
    renderMessage(message) {
        return <p>{message.msg}</p>
    },
    inputChange() {
        this.setState({
            input: this.refs.inputInput.value
        })
    },
    inputSubmit(e) {
        e.preventDefault()
        this.sock.send(newMessage(this.state.input))
        this.setState({input: null})
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

$(function() {
    var app = $('#app')
    if (app.length) {
        ReactDOM.render(<Conversation />, app[0])
    }
})
