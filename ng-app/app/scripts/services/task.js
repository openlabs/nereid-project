'use strict';

angular.module('nereidProjectApp')
  .factory('Task', [
    '$http',
    'nereid',
    function($http, nereid) {

    var Task = this;

    Task.get = function(projectId, taskId) {
      return $http.get(nereid.buildUrl('/project-' + projectId + '/task-' + taskId));
    };

    Task.addComment = function(taskId, commentObj) {
      return $http.post(nereid.buildUrl('/task-' + taskId + '/-update'), commentObj);
    };

    Task.create = function(projectId, taskObj) {
      return $http.post(nereid.buildUrl('/projects/' + projectId + '/tasks'), taskObj);
    };

    Task.states = [
      {value: 'Backlog', text: 'Backlog'},
      {value: 'Planning', text: 'Planning'},
      {value: 'In Progress', text: 'In Progress'},
      {value: 'Review', text: 'Review'},
      {value: 'Done', text: 'Done'}
    ];
    Task.progressStates = [
      'Backlog', 'Planning', 'In Progress', 'Review'
    ];

    return Task;
  }
]);
