'use strict';

var gulp = require('gulp');
var karma = require('gulp-karma');
var jshint = require('gulp-jshint');

gulp.task('lint', function() {
  return gulp.src(['app/scripts/**/*.js', 'test/spec/**/*.js'])
    .pipe(jshint())
    .pipe(jshint.reporter('jshint-stylish'));
  });

gulp.task('test', function() {
  //Be sure to return the stream
  return gulp.src('_')
  .pipe(karma({
    configFile: 'karma.conf.js',
    action: 'run'
  }))
  .on('error', function(err) {
      // Make sure failed tests cause gulp to exit non-zero
      throw err;
    });
  });

gulp.task('default', ['lint', 'test'], function() {
  // place code for your default task here
});
