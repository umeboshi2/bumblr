# require config comes first
require.config
  baseUrl: 'javascripts/bumblr'
  paths:
    jquery: '../../../components/jquery/dist/jquery'
    underscore: '../../../components/lodash/dist/lodash.compat'
    backbone: '../../../components/backbone/backbone'
    'backbone.babysitter': '../../../components/backbone.babysitter/lib/backbone.babysitter'
    'backbone.wreqr': '../../../components/backbone.wreqr/lib/backbone.wreqr'
    marionette: '../../../components/marionette/lib/core/backbone.marionette'
    validation: '../../../components/backbone.validation/dist/backbone-validation-amd'
    bootstrap: '../../../components/bootstrap/dist/js/bootstrap'
    moment: '../../../components/moment/moment'
    fullcalendar: '../../../components/fullcalendar/dist/fullcalendar'
    'jquery-ui': '../../../components/jquery-ui/jquery-ui'
    requirejs: '../../../components/requirejs/require'
    text: '../../../components/requirejs-text/text'
    teacup: '../../../components/teacup/lib/teacup'
    marked: '../../../components/marked/lib/marked'
    querystring: '../../../components/query-string/query-string'
    #oauth: '../../../components/oauth-1.0a/index'
    #request: '../../../components/request'
    oauth: '../../../components/oauth-js/dist/oauth.min'
    'backbone.paginator': '../../../components/backbone.paginator/lib/backbone.paginator'
    
    
  # FIXME:  try to reduce the shim to only the
  # necessary resources
  shim:
    jquery:
      exports: ['$', 'jQuery']
    bootstrap:
      deps: ['jquery']
    underscore:
      exports: '_'
    backbone:
      deps: ['jquery', 'underscore']
      exports: 'Backbone'
    marionette:
      deps: ['jquery', 'underscore', 'backbone']
      exports: 'Marionette'
    #qs:
    #  exports: 'Qs'
require [
  'application'
  'frontdoor/main'
  'demoapp/main'
  ], (App) ->
  # debug
  window.app = App

  # wait until app is ready before starting  
  start_app_one = () ->
    if App.ready == false
      setTimeout(start_app_two, 100)
    else
      App.start()
        
  start_app_two = () ->
    if App.ready == false
      setTimeout(start_app_one, 100)
    else
      App.start()
    
  start_app_one()
  return App
        
        