'use strict';

angular.module('nereidProjectApp', [
  'ui.router',
  'ngMaterial',
  'openlabs.angular-nereid-auth',
  'cfp.hotkeys',
  'infinite-scroll',
  'ng-mfb',
  'ui.gravatar',
  'hc.marked',
  'angular.filter'
  ])
  .config(function($stateProvider, $urlRouterProvider, $mdThemingProvider, markedProvider) {

    // Show syntax highlighting in markdown `code`
    markedProvider.setOptions({
      gfm: true,
      tables: true,
      highlight: function (code) {
        return window.hljs.highlightAuto(code).value;
      }
    });

    $urlRouterProvider
      .when('', '/')
      .when('/', '/projects')
      .otherwise('/404');

    $stateProvider
      .state('login', {
        url: '/login',
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        publicAccess: true
      })

      .state('404', {
        url: '/404',
        templateUrl: 'views/404.html'
      })

      .state('base', {
        url: '/',
        templateUrl: 'views/base.html',
        controller: 'BaseCtrl'
      })

      .state('task', {
        // This state redirects to `base.project.task`
        url: '/tasks/{taskId:int}',
        controller: function($state, Project) {
          Project.go({taskId: $state.params.taskId});
        }
      })

      .state('base.projects', {
        url: 'projects',
        views: {
          'sidenav': {
            templateUrl: 'views/base-sidenav.html',
          },
          'main-view': {
            templateUrl: 'views/projects.html',
            controller: 'ProjectsCtrl'
          }
        }
      })

      .state('base.project', {
        url: 'projects/{projectId:int}',
        views: {
          'sidenav': {
            templateUrl: 'views/project-sidenav.html',
          },
          'main-view': {
            templateUrl: 'views/project.html',
            controller: 'ProjectCtrl'
          }
        }
      })

      .state('base.myTasks', {
        url: 'my-tasks',
        views: {
          'sidenav': {
            templateUrl: 'views/base-sidenav.html',
          },
          'main-view': {
            templateUrl: 'views/my-tasks.html',
            controller: 'MyTasksCtrl'
          }
        }
      })

      .state('base.project.tasks', {
        url: '/tasks',
        views: {
          'project-nav-view': {
            templateUrl: 'views/tasks.html',
            controller: 'TasksCtrl'
          }
        }
      })

      .state('base.project.task', {
        url: '/tasks/{taskId:int}',
        views: {
          'project-nav-view': {
            templateUrl: 'views/task.html',
            controller: 'TaskCtrl'
          }
        }
      })

      .state('base.project.tasks.open', {
        url: '/open',
        tabIndex: 0, // Tab index of the md-tab in tasks view
        views: {
          'task-tabs': {
            templateUrl: 'views/project-open-tasks.html',
            controller: 'ProjectOpenTasksCtrl'
          }
        }
      })

      .state('base.project.tasks.all', {
        url: '/all',
        tabIndex: 1,
        views: {
          'task-tabs': {
            templateUrl: 'views/all-tasks.html',
            controller: 'AllTasksCtrl'
          }
        }
      })

      .state('base.project.tasks.my', {
        url: '/my',
        tabIndex: 2,
        views: {
          'task-tabs': {
            templateUrl: 'views/project-my-tasks.html',
            controller: 'ProjectMyTasksCtrl'
          }
        }
      })

      .state('base.iterations', {
        url: 'iterations',
        views: {
          'sidenav': {
            templateUrl: 'views/base-sidenav.html',
          },
          'main-view': {
            templateUrl: 'views/iterations.html',
            controller: 'IterationsCtrl'
          }
        }
      })

      .state('base.iteration', {
        url: 'iterations/{iterationId:int}',
        views: {
          'sidenav': {
            templateUrl: 'views/base-sidenav.html',
          },
          'main-view': {
            templateUrl: 'views/iteration.html',
            controller: 'IterationCtrl'
          }
        }
      })

      .state('base.open_tasks', {
        url: 'open-tasks',
        views: {
          'sidenav': {
            templateUrl: 'views/base-sidenav.html',
          },
          'main-view': {
            templateUrl: 'views/open-tasks.html',
            controller: 'OpenTasksCtrl'
          }
        }
      });

      $mdThemingProvider.theme('default')
      .primaryPalette('light-blue', {
        'default': '500'
      })
      .accentPalette('pink');
      $mdThemingProvider.theme('input', 'default')
      .primaryPalette('grey');
  })
  .run(['$rootScope', '$state', 'nereidAuth', 'nereid', function ($rootScope, $state, nereidAuth, nereid) {
    if (window.MacGap !== undefined) {
      // If this app is loaded from MacGap application
      // first set the ApiBasePath to load data from.
      $.getJSON('../config.json', function(data){
        nereid.setApiBasePath(data['apiBasePath']);
      });
      // Maximize mac app to fill the user's screen
      MacGap.Window.maximize();
    }
    nereidAuth.refreshUserInfo(); // XXX: why?

    $rootScope.$on('$stateChangeSuccess', function(event, toState) {
      if (!toState.publicAccess && !nereidAuth.isLoggedIn()) {
        // Redirect to login page if viewing non public page and not logged-In.
        $state.go('login');
      }
    });

    $rootScope.$on('nereid-auth:loginRequired', function () {
      nereidAuth.logoutUser();
    });

    $rootScope.$on('nereid-auth:logout', function () {
      $state.go('login');
    });
  }]);

angular.module('ui.gravatar').config([
  'gravatarServiceProvider', function(gravatarServiceProvider) {
    gravatarServiceProvider.defaults = {
      size : 100,
      'default': 'mm'  // Mystery man as default for missing avatars
    };

    // Use https endpoint
    gravatarServiceProvider.secure = true;

    // Force protocol
    gravatarServiceProvider.protocol = 'my-protocol';
  }
]);
