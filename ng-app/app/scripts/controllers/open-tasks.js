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
        .success(function(response){
          $scope.tasks = response.tasks;
          $scope.employees = response.employees;
          $scope.users = response.users;
          $scope.projects = response.projects;

          // Group tasks
          $scope.taskByEmployee = [];
          $scope.taskByProject = [];
          $scope.taskByUser = [];
          angular.forEach($scope.employees, function(employee) {
            $scope.taskByEmployee.push({
              name: employee.displayName,
              tasks: $scope.tasks.filter(function(task) {
                return task.assigned_to && (task.assigned_to.id === employee.id);
              })
            });
          });

          angular.forEach($scope.users, function(user) {
            $scope.taskByUser.push({
              name: user.displayName,
              tasks: $scope.tasks.filter(function(task) {
                return task.assigned_to && (task.assigned_to.id === user.id);
              })
            });
          });

          angular.forEach($scope.projects, function(project) {
            $scope.taskByProject.push({
              name: project.name,
              tasks: $scope.tasks.filter(function(task) {
                return task.project.id === project.id;
              })
            });
          });

        })
        .finally(function() {
          $scope.loadingTasks = false;
        });

      $scope.groupOptions = [
        'Project',
        'Employee',
        'User'
      ];
      // By default group by employee
      $scope.groupOption = 'Employee';


    }
  ]);

