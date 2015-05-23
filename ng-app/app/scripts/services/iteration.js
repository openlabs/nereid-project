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

    Iteration.groups = [
      'Owner',
      'Assignee',
      'Project'
    ];

    return Iteration;
  }
]);
