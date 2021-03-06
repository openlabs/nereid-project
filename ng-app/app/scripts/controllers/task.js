'use strict';

angular.module('nereidProjectApp')
.controller('TaskCtrl', [
    '$scope',
    '$state',
    'Task',
    'Helper',
    'nereidAuth',
    function($scope, $state, Task, Helper, nereidAuth) {

      $scope.taskId = $state.params.taskId;
      $scope.projectId = $state.params.projectId;
      $scope.commentObj = {};
      $scope.user = nereidAuth.user();

      $scope.states = Task.states;

      $scope.loadTask = function() {
        $scope.loadingTask = true;
        Task.get($scope.projectId, $scope.taskId)
          .success(function(result) {
            $scope.task = result;
            angular.extend($scope.commentObj, {
              progress_state: result.progress_state,
              assigned_to: result.assigned_to && result.assigned_to.id
            });
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch task', reason);
          })
          .finally(function() {
            $scope.loadingTask = false;
          });
      };

      $scope.submitComment = function() {
        $scope.savingComment = true;
        Task.addComment($scope.projectId, $scope.taskId, $scope.commentObj)
          .success(function(result) {
            $scope.task.comments = $scope.task.comments.concat(result.items);
            $scope.commentObj.comment = null;
          })
          .error(function(reason) {
            Helper.showDialog('Could not add comment', reason);
          })
          .finally(function() {
            $scope.savingComment = false;
          });
      };

    }
  ]);
