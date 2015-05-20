'use strict';

angular.module('nereidProjectApp')
.controller('AllTasksCtrl', [
    '$scope',
    'Task',
    function($scope, Task) {
      $scope.loadTasks = function() {
      };
    }
  ]);
