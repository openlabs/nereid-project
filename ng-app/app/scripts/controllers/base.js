'use strict';

angular.module('nereidProjectApp')
.controller('BaseCtrl', [
    '$scope',
    'hotkeys',
    function($scope, hotkeys) {
      //TODO: Handle global search

      hotkeys.add({
        combo: '/',
        description: 'Display the search box',
        callback: function() {
          $scope.showGlobalSearch = true;
        }
      });

    }
  ]);
