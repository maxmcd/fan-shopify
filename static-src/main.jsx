
const render = ReactDOM.render
const Router = ReactRouter.Router
const Route = ReactRouter.Route
const Link = ReactRouter.Link
const browserHistory = ReactRouter.browserHistory


let navStyle = {
    backgroundColor: "#eeeeee"
}

const Navbar = (props) => {
    return (
        <header className="navbar navbar-static-top" style={navStyle}>
            <div className="container">
                <div className="navbar-header"> 
                    <Link className="navbar-brand" to={`/app/`}>Kayobe</Link>
                </div>
                <nav clasName="navbar navbar-default">
                    <div className="container-fluid">
                        <div className="collapse navbar-collapse">
                            <ul className="nav navbar-nav">
                                <li><Link to={`/app/`} activeClassName="active">Dashboard</Link></li>
                                <li><Link to={`/app/templates/`} activeClassName="active">Templates</Link></li>
                                <li><Link to={`/app/events/`} activeClassName="active">Events</Link></li>
                                <li><Link to={`/app/data/`} activeClassName="active">Data</Link></li>
                                <li className="dropdown">
                                    <a href="#" className="dropdown-toggle" data-toggle="dropdown">
                                        {props.email} <span className="caret"></span>
                                    </a>
                                    <ul className="dropdown-menu">
                                        <li><Link to={`/app/settings/`} activeClassName="active">Settings</Link></li>
                                        <li className="divider"></li>
                                        <li><a href="/logout/">Log Out</a></li>
                                    </ul>
                                </li>
                            </ul>
                        </div>
                    </div>
                </nav>
            </div>
        </header>
    )
}

const App = React.createClass({
    getInitialState() {
        return window.reactData
    },
    render() {
        return (
            <div>
                <Navbar email={this.state.user.email}/>
                <div className="container">
                    <div className="detail" onClick={this.bump}>
                        {this.props.children && React.cloneElement(this.props.children, {
                            reactData: this.state,
                        })}
                    </div>
                </div>
            </div>
        )
    }
})

const Dashboard = React.createClass({
  render() {
    return (
      <div>
        <h2>Dash</h2>
      </div>
    )
  }
})

const User = React.createClass({
  render() {
    return (
      <div>
        <h2>{this.props.params.userId}</h2>
      </div>
    )
  }
})

const Templates = React.createClass({
  render() {
    return (
      <div>
        <h2>Templates</h2>
      </div>
    )
  }
})

const Events = React.createClass({
  render() {
    return (
      <div>
        <h2>Events</h2>
      </div>
    )
  }
})

const Data = React.createClass({
  render() {
    return (
      <div>
        <h2>Data</h2>
      </div>
    )
  }
})

const Settings = React.createClass({
  render() {
    console.log(this)
    return (
      <div>
        <h2>Settings</h2>
        {this.props.reactData.count}
      </div>
    )
  }
})

const FourOhFour = React.createClass({
  render() {
    return (
      <div>
        <h2>404 :(</h2>
        <p>Whoops! Looks like that page doesn't exist.</p>
        <p><a href="/app/">Take me home.</a></p>
      </div>
    )
  }
})

$(function() {
    render((
      <Router history={browserHistory}>
        <Route path="/" component={App}>
            <Route path="/app/" component={Dashboard}/>
            <Route path="/app/templates/" component={Templates}/>
            <Route path="/app/events/" component={Events}/>
            <Route path="/app/data/" component={Data}/>
            <Route path="/app/settings/" component={Settings}/>
            <Route path="/app/user/:userId" component={User}/>
            <Route path="*" component={FourOhFour}/>
        </Route>
      </Router>
    ), document.getElementById('app'))
})
