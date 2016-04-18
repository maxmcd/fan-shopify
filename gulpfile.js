var gulp = require('gulp'),
    gae = require('gulp-gae'),
    watch = require('gulp-watch'),
    sass = require('gulp-sass'),
    gutil = require('gulp-util')
    plumber = require('gulp-plumber')
    babel = require('gulp-babel'),
    concat = require('gulp-concat'),
    httpProxy = require('http-proxy'),
    http = require('http'),
    gutil = require('gulp-util'),
    spawn = require('child_process').spawn,
    mainBowerFiles = require('main-bower-files');


gulp.task('pushpin', function (cb) {
    gutil.log(gutil.colors.green('Starting pushpin server'))
    spawn('pushpin', ['--config=.pushpin/pushpin.conf']);
    // we're blind here, use the logs dir in .pushpin/log
})

gulp.task('proxy', function() {

    // app engine broadcasts on 8546
    var proxy = new httpProxy.createProxyServer({
        target: {
            host: 'localhost',
            port: 8546
        }
    });

    // pushpin broadcasts on 7999
    // we'll proxy our websocket requests through pushpin
    var wsProxy = new httpProxy.createProxyServer({
        target: {
            host: 'localhost',
            port: 7999, 
        }
    })
    var proxyServer = http.createServer(function(req, res) {
        proxy.web(req, res);
    });

    proxyServer.on('upgrade', function(req, socket, head) {
        wsProxy.ws(req, socket, head);
    });

    proxyServer.listen(8081);
    gutil.log(gutil.colors.green('Proxy server started at localhost:8081'))
})

gulp.task('gae-serve', function() {
    gulp.src('app.yaml')
        .pipe(gae('dev_appserver.py', [], {
            port: 8546,
            host: 'localhost',
            admin_port: 8001,
            api_port: 8547,
            admin_host: 'localhost',
            allow_skipped_files: true,
        }));
});

gulp.task('vendor', function() {
    gulp.src(mainBowerFiles({
        filter: e => e.split('.').pop() === "js"
    })).pipe(concat('vendor.js'))
        .pipe(gulp.dest('static'));

    gulp.src(mainBowerFiles({
        filter: e => e.split('.').pop() === "css"
    })).pipe(concat('vendor.css'))
        .pipe(gulp.dest('static'));

})

gulp.task('js', function() {
    return gulp.src('static-src/*.js*')
        .pipe(plumber())
        .pipe(babel({
            presets: ['es2015','react']
        }))
        .on('error', (e) => {
            gutil.log(e.stack)
        })
        .pipe(concat('client.js'))
        .pipe(gulp.dest('static'));
})

gulp.task('css', function() {
    return gulp.src('static-src/*.sass')
        .pipe(sass().on('error', sass.logError))
        .pipe(concat('client.css'))
        .pipe(gulp.dest('static'));
});

gulp.task('watch', function () {
    watch('static-src/*.js*', function () {
        gulp.start('js');
    });
    watch('static-src/*.sass', function () {
        gulp.start('css');
    });
});

gulp.task('default', [
    'vendor',
    'js',
    'css',
    'watch',
    'pushpin',
    'gae-serve',
    'proxy',
]);