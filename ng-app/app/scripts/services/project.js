'use strict';

angular.module('nereidProjectApp')
  .factory('Project', [
    '$http',
    'nereid',
    function ($http, nereid) {

    var Project = this;

    Project.getAll = function() {
      return $http.get(nereid.buildUrl('/projects'));
    };

    Project.get = function(projectId) {
      return $http.get(nereid.buildUrl('/project-' + projectId));
    };

    Project.getTasks = function(projectId) {
      return $http.get(nereid.buildUrl('/projects/' + projectId + '/tasks'));
    };

    return Project;
  }
]);
