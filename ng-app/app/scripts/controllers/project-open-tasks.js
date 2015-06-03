'use strict';

angular.module('nereidProjectApp')
.controller('ProjectOpenTasksCtrl', [
    '$scope',
    'Task',
    'Project',
    'Helper',
    function($scope, Task, Project, Helper) {
      $scope.progressStates = Task.progressStates;
      $scope.tasks = [];

      $scope.loadProjectsOpenTasks = function(page) {
        $scope.loadingTasks = true;
        var filter = {
          state: 'opened',
          page: page
        };
        Project.getTasks($scope.projectId, filter)
          .success(function(result) {
            $scope.tasks = $scope.tasks.concat(result.items);
            if(result.pages > result.page) {
              $scope.loadProjectsOpenTasks(page + 1);
            }
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

