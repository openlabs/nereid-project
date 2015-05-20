'use strict';

angular.module('nereidProjectApp')
.controller('AllTasksCtrl', [
    '$mdDialog',
    '$scope',
    'Project',
    function($mdDialog, $scope, Project) {

      $scope.loadTasks = function(projectId) {
        Project.getTasks(projectId)
          .success(function(result) {
            $scope.tasks = result.items;
          })
          .error(function(reason) {
            $mdDialog.alert()
            .title('Could not fetch tasks')
            .content(reason)
            .ariaLabel('Could not fetch tasks')
            .ok('Got it!');
          });
      };

    }
  ]);
