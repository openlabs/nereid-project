'use strict';

angular.module('nereidProjectApp')
.controller('OpenTasksCtrl', [
    '$scope',
    'Project',
    'Helper',
    function($scope, Project, Helper) {

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
