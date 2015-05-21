'use strict';

angular.module('nereidProjectApp')
  .factory('Helper', [
    '$http',
    '$mdDialog',
    '$mdToast',
    function($http, $mdDialog, $mdToast) {

      var Helper = this;

      Helper.showToast = function(message, time) {
        $mdToast.show(
          $mdToast.simple()
            .content(message)
            .position('top right')
            .action('OK')
            .hideDelay(time || 2000)
        );
      };

      Helper.showDialog = function(title, content) {
        $mdDialog.show(
          $mdDialog.alert()
            .title(title)
            .content(content)
            .ariaLabel(title)
            .ok('Got it!')
        );
      };

    return Helper;
  }
]);
