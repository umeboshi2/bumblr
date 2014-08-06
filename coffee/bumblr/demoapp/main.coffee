#
define (require, exports, module) ->
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'

  Controller = require 'demoapp/controller'
  

  class Router extends Backbone.Marionette.AppRouter
    appRoutes:
      'demo': 'start'
      'demo/dashboard': 'show_dashboard'
      'demo/viewmeeting/:id': 'show_meeting'
      'demo/listmeetings': 'list_meetings'
      
  current_calendar_date = undefined
  MSGBUS.commands.setHandler 'demo:maincalendar:set_date', () ->
    cal = $ '#maincalendar'
    current_calendar_date = cal.fullCalendar 'getDate'

  MSGBUS.reqres.setHandler 'demo:maincalendar:get_date', () ->
    current_calendar_date
    
  MSGBUS.commands.setHandler 'demo:route', () ->
    #window.msgbus = MSGBUS
    console.log "demo:route being handled..."
    controller = new Controller
    router = new Router
      controller: controller
      