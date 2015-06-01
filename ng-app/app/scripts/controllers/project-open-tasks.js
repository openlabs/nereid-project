'use strict';

angular.module('nereidProjectApp')
.controller('ProjectOpenTasksCtrl', [
    '$scope',
    'Task',
    'Project',
    'Helper',
    function($scope, Task, Project, Helper) {
      $scope.progressStates = Task.progressStates;

      $scope.loadProjectsOpenTasks = function() {
        $scope.loadingTasks = true;
        var filter = {
          state: 'opened',
          per_page: 200
        };
        Project.getTasks($scope.projectId, filter)
          .success(function(result) {
            $scope.tasks = result.items;
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch open tasks', reason);
          })
          .finally(function() {
            $scope.loadingTasks = false;
          });
      };

    }
  ]);

