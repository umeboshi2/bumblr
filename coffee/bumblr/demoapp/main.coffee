#
define (require, exports, module) ->
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'

  Controller = require 'demoapp/controller'
  

  class Router extends Backbone.Marionette.AppRouter
    appRoutes:
      'demo': 'start'
      'demo/dashboard': 'show_dashboard'
      'demo/listblogs': 'list_blogs'
      'demo/viewblog/:id': 'view_blog'
      
  current_calendar_date = undefined
  MSGBUS.commands.setHandler 'demo:maincalendar:set_date', () ->
    cal = $ '#maincalendar'
    current_calendar_date = cal.fullCalendar 'getDate'

  MSGBUS.reqres.setHandler 'demo:maincalendar:get_date', () ->
    current_calendar_date
    
  MSGBUS.commands.setHandler 'demo:route', () ->
    console.log "demo:route being handled..."
    controller = new Controller
    router = new Router
      controller: controller
      
