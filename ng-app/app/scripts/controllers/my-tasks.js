'use strict';

angular.module('nereidProjectApp')
.controller('MyTasksCtrl', [
    '$mdDialog',
    '$scope',
    'Task',
    'Helper',
    function($mdDialog, $scope, Task, Helper) {
      $scope.progressStates = Task.progressStates;

      $scope.loadMyTasks = function() {
        $scope.loadingTasks = true;
        Task.getMyTasks()
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
