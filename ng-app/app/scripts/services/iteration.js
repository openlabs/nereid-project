'use strict';

angular.module('nereidProjectApp')
  .factory('Iteration', [
    '$http',
    'nereid',
    function($http, nereid) {

    var Iteration = this;

    Iteration.getAll = function() {
      return $http.get(nereid.buildUrl('/iterations/'));
    };

    Iteration.get = function(iterationId) {
      return $http.get(nereid.buildUrl('/iterations/' + iterationId));
    };

    Iteration.get = function(iterationId) {
      return $http.get(nereid.buildUrl('/iterations/' + iterationId));
    };

    Iteration.groupBy = function(groupBy, iterationId) {
      if(groupBy === 'Owner') {
        return $http.get(nereid.buildUrl('/iterations/' + iterationId + '/stats/tasks_by_user'))
          .success(function(result) {
            result.tasks = result.tasks_by_user;
          });
      } else if(groupBy === 'Project') {
        return $http.get(nereid.buildUrl('/iterations/' + iterationId + '/stats/tasks_by_project'))
          .success(function(result) {
            result.tasks = result.tasks_by_project;
          });
      }
    };

    Iteration.groups = [
      'Owner',
      'Project'
    ];

    return Iteration;
  }
]);
