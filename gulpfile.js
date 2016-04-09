var gulp = require('gulp'),
    gae = require('gulp-gae'),
    watch = require('gulp-watch'),
    sass = require('gulp-sass'),
    gutil = require('gulp-util')
    plumber = require('gulp-plumber')
    babel = require('gulp-babel'),
    concat = require('gulp-concat'),
    spawn = require('child_process').spawn,
    mainBowerFiles = require('main-bower-files');


gulp.task('pushpin', function (cb) {
    // spawn('pushpin', ['--config=.pushpin/pushpin.conf']);
    // we're blind here, use the logs dir in .pushpin/log
})

gulp.task('gae-serve', function() {
    gulp.src('app.yaml')
        .pipe(gae('dev_appserver.py', [], {
            port: 8546,
            host: 'localhost',
            admin_port: 8001,
            admin_host: 'localhost'
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
]);