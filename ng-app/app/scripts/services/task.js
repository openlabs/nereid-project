'use strict';

angular.module('nereidProjectApp')
  .factory('Task', [
    '$http',
    'nereid',
    'nereidAuth',
    function($http, nereid, nereidAuth) {

    var Task = this;

    Task.get = function(projectId, taskId) {
      return $http.get(nereid.buildUrl('/projects/' + projectId + '/tasks/' + taskId + '/'));
    };

    Task.getMyTasks = function() {
      var userId = nereidAuth.user().id;
      return $http.get(nereid.buildUrl('/users/' + userId + '/tasks' + '/'));
    };

    Task.addComment = function(projectId, taskId, commentObj) {
      return $http.post(nereid.buildUrl('/projects/' + projectId + '/tasks/' + taskId + '/updates/'), {params: commentObj});
    };

    Task.create = function(projectId, taskObj) {
      return $http.post(nereid.buildUrl('/projects/' + projectId + '/tasks/'), taskObj);
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
