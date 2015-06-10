'use strict';

angular.module('nereidProjectApp')
.controller('ProjectMyTasksCtrl', [
    '$scope',
    'nereidAuth',
    'Task',
    'Project',
    'Helper',
    function($scope, nereidAuth, Task, Project, Helper) {
      $scope.progressStates = Task.progressStates;
      $scope.userId = nereidAuth.user().id;

      $scope.loadMyTasks = function() {
        $scope.loadingTasks = true;
        var filter = {
          project: $scope.projectId
        };
        Task.getMyTasks($scope.userId, filter)
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

