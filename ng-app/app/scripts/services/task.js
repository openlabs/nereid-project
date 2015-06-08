'use strict';

angular.module('nereidProjectApp')
  .factory('Task', [
    '$http',
    '$q',
    'nereid',
    function($http, $q, nereid) {

    var Task = this;

    Task.get = function(projectId, taskId) {
      return $http.get(nereid.buildUrl('/projects/' + projectId + '/tasks/' + taskId + '/'));
    };

    Task.getOpenTasks = function() {
      return $http.get(nereid.buildUrl('/open-tasks'));
    };

    Task.getMyTasks = function(userId, filter) {
      return $http.get(nereid.buildUrl('/users/' + userId + '/tasks' + '/'), {params: filter});
    };

    Task.addComment = function(projectId, taskId, commentObj) {
      return $http.post(nereid.buildUrl('/projects/' + projectId + '/tasks/' + taskId + '/updates/'), commentObj);
    };

    Task.getProjectId = function(taskId) {
      var deferred = $q.defer();
      $http.get(nereid.buildUrl('/tasks/' + taskId))
      .success(function(data){
        deferred.resolve(data.parent);
      });
      return deferred.promise;
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

    Task.subTypes = [
      {value: 'feature', text: 'Feature'},
      {value: 'bug', text: 'Bug'},
      {value: 'question', text: 'Question'},
      {value: 'epic', text: 'Epic'},
    ];


    Task.progressStates = [
      'Backlog', 'Planning', 'In Progress', 'Review'
    ];

    return Task;
  }
]);
