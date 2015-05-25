'use strict';

angular.module('nereidProjectApp')
.controller('IterationCtrl', [
    '$scope',
    '$state',
    'Iteration',
    'Helper',
    'Task',
    function($scope, $state, Iteration, Helper, Task) {
      $scope.progressStates = Task.progressStates;
      $scope.groups = Iteration.groups;

      $scope.loadIteration = function() {
        $scope.loadingIteration = true;
        Iteration.get($state.params.iterationId)
          .success(function(result) {
            $scope.iteration = result;
            $scope.doneTasks =  $scope.iteration.tasks.filter(function(task) {
              return task.progress_state === 'Done';
            });
            // By default group by owner
            $scope.groupIteration('Owner');
          })
          .error(function(reason) {
            Helper.showDialog('Could not fetch iteration.', reason);
          })
          .finally(function() {
            $scope.loadingIteration = false;
          });
      };

      $scope.groupIteration = function(groupBy) {
        $scope.groupBy = groupBy;
        Iteration.groupBy(groupBy, $state.params.iterationId)
          .then(function(result) {
            $scope.iterationStats = [];
            var taskGroup = result.data.tasks;
            angular.forEach(taskGroup, function(tasks, key) {
              var iterationStat = {
                name: key
              };
              iterationStat.totalTasks = tasks.length;
              // Set count of each state
              iterationStat.backlogTasksCount = tasks.filter(function(task) { return task.progress_state === 'Backlog'; }).length;
              iterationStat.planningTasksCount = tasks.filter(function(task) { return task.progress_state === 'Planning'; }).length;
              iterationStat.inProgressTasksCount = tasks.filter(function(task) { return task.progress_state === 'In Progress'; }).length;
              iterationStat.reviewTasksCount = tasks.filter(function(task) { return task.progress_state === 'Review'; }).length;
              iterationStat.doneTasksCount = tasks.filter(function(task) { return task.state === 'Done'; }).length;
              $scope.iterationStats.push(iterationStat);
            });
          }, function(reason) {
            Helper.showDialog('Could not fetch iteration.', reason);
          });
      };

    }
  ]);
