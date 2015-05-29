'use strict';

angular.module('nereidProjectApp')
.controller('OpenTasksCtrl', [
    '$scope',
    'Task',
    function($scope, Task) {
      $scope.progressStates = Task.progressStates;

      // Fetch all open tasks
      $scope.loadingTasks = true;
      Task.getOpenTasks()
        .then(function(response){
          $scope.tasks = response.data.tasks;
          $scope.employees = response.data.employees;
          $scope.users = response.data.users;
          $scope.projects = response.data.projects;
          $scope.loadingTasks = false;
      });

      $scope.groupOptions = [
        'Project',
        'Employee',
        'User'
      ];
      $scope.groupOption = 'Employee';
    }
  ]);

