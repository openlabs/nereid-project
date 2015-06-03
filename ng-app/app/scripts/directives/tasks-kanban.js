'use strict';

/*
 * Dirctive for showing kanban view of the prgress states of tasks.
 *
 * type: my-tasks/open
 * tasks: Array of tasks to show in kanban view
 * projectId: Get tasks specific to the projectId provided
 */

angular.module('nereidProjectApp')
  .directive('tasksKanban', [
    'Helper',
    'Task',
    'Project',
    function (Helper, Task) {
      return {
        restrict: 'E',
        transclude: true,
        scope: {
          projectId: '@',
          type: '@',
          tasks: '='
        },
        templateUrl: 'views/tasks-kanban.html',
        link: function (scope) {
          scope.progressStates = Task.progressStates;
          scope.$watch('tasks', function() {
            scope.kanbanTasks = scope.tasks;
          });

        }
      };
    }]);
