'use strict';

angular.module('nereidProjectApp')
  .factory('Project', [
    '$http',
    'nereid',
    function ($http, nereid) {

    var Project = this;

    Project.getTasks = function(projectId) {
      return $http.get(nereid.buildUrl('/projects/' + projectId + '/tasks'));
    };

    return Project;
  }
]);
