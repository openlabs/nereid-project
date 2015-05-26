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
    function (Helper, Task, Project) {
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
          scope.kanbanTasks = scope.tasks;

          scope.loadMyTasks = function() {
            var filter = {
              state: 'opened',
              per_page: 200
            };
            if(scope.projectId) {
              filter.project = scope.projectId;
            }
            Task.getMyTasks(filter)
              .success(function(result) {
                scope.kanbanTasks = result.items;
              })
              .error(function(reason) {
                Helper.showDialog('Could not fetch your tasks', reason);
              });
          };

          scope.loadProjectsOpenTasks = function() {
            var filter = {
              state: 'opened',
              per_page: 200
            };
            Project.getTasks(scope.projectId, filter)
              .success(function(result) {
                scope.kanbanTasks = result.items;
              })
              .error(function(reason) {
                Helper.showDialog('Could not fetch open tasks', reason);
              });
          };

          if(scope.type === 'my-tasks') {
            scope.loadMyTasks();
          } else if(scope.type === 'open') {
            scope.loadProjectsOpenTasks();
          }

        }
      };
    }]);
