'use strict';

angular.module('nereidProjectApp')
.controller('MyTasksCtrl', [
    '$mdDialog',
    '$scope',
    'nereidAuth',
    'Task',
    'Helper',
    function($mdDialog, $scope, nereidAuth, Task, Helper) {
      $scope.progressStates = Task.progressStates;
      $scope.userId = nereidAuth.user().id;

      $scope.loadMyTasks = function() {
        $scope.loadingTasks = true;
        Task.getMyTasks($scope.userId)
          .success(function(result) {
            $scope.tasks = result.items;
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch your tasks', reason);
          })
          .finally(function() {
            $scope.loadingTasks = false;
          });
      };

    }
  ]);
