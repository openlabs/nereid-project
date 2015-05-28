'use strict';

angular.module('nereidProjectApp')
  .factory('Project', [
    '$http',
    '$state',
    '$mdDialog',
    'nereid',
    'Task',
    function ($http, $state, $mdDialog, nereid, Task) {

    var Project = this;

    Project.getAll = function() {
      // Returns all projects.
      // TODO: This means going through all pages
      // For the moment just handle 50
      return Project.getProjects(1, 50);
    };

    Project.getProjects = function(page, per_page) {
      if (page === undefined) {
        page=1;
      }
      if (per_page === undefined) {
        per_page=20;
      }
      return $http.get(nereid.buildUrl(
        '/projects/?page=' + page + '&per_page=' + per_page
      ));
    };

    Project.get = function(projectId) {
      return $http.get(nereid.buildUrl('/projects/' + projectId + '/'));
    };

    Project.getTasks = function(projectId, filter) {
      filter = filter || {};
      return $http.get(nereid.buildUrl('/projects/' + projectId + '/tasks/'), {params: filter});
    };


    Project.go = function(selection) {
      if (selection.taskId) {
        var taskId = selection.taskId;
        // If a task ID is defined, this was an attempt to go to that task.
        Task.getProjectId(taskId)
        .then(function(projectId) {
          $state.go('base.project.task', {
            taskId: taskId,
            projectId: projectId
          });
        });
      } else {
        $state.go('base.project', {projectId: selection.id});
      }
      $mdDialog.hide();
    };

    return Project;
  }
]);
