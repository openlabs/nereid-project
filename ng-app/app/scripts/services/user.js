'use strict';

angular.module('nereidProjectApp')
  .factory('User', [
    '$http',
    '$q',
    'nereid',
    function($http, $q, nereid) {

    var User = this;

    User.changePassword = function(passwordObj) {
      return $http.post(nereid.buildUrl('/change-password'), passwordObj);
    };

    return User;
  }
]);
