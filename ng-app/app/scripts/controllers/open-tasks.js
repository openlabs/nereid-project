'use strict';

angular.module('nereidProjectApp')
.controller('OpenTasksCtrl', [
    '$scope',
    'Project',
    'Helper',
    'Task',
    function($scope, Project, Helper, Task) {

      $scope.progressStates = Task.progressStates;

      $scope.getOpenTasks = function(projectId) {
        var filter = {
          state: 'opened'
        };
        Project.getTasks(projectId, filter)
          .success(function(result) {
            $scope.tasks = result.items;
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch open tasks', reason);
          });
      };


    }
  ]);
