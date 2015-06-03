'use strict';

angular.module('nereidProjectApp')
.controller('ProjectMyTasksCtrl', [
    '$scope',
    'Task',
    'Project',
    'Helper',
    function($scope, Task, Project, Helper) {
      $scope.progressStates = Task.progressStates;

      $scope.loadMyTasks = function() {
        $scope.loadingTasks = true;
        var filter = {
          project: $scope.projectId,
          state: 'opened',
          per_page: 200
        };
        Task.getMyTasks(filter)
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

