'use strict';

angular.module('nereidProjectApp')
.controller('MyTasksCtrl', [
    '$mdDialog',
    '$scope',
    'Task',
    'Helper',
    function($mdDialog, $scope, Task, Helper) {

      $scope.loadMyTasks = function() {
        var filter = {
          project: $scope.projectId
        };
        Task.getMyTasks(filter)
          .success(function(result) {
            $scope.tasks = result.items;
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch your tasks', reason);
          });
      };

    }
  ]);
