define (require, exports, module) ->
  Backbone = require 'backbone'
  Marionette = require 'marionette'
  MSGBUS = require 'msgbus'
  Views = require 'views/mainviews'

  HubbyBrand = new Backbone.Model
    name: 'Hubby'
    url: '#'
    
    
  initialize_page = () ->
    console.log 'initialize_page'
    layout = new Views.MainPageLayout
    layout.on 'show', =>
      view = new Views.MainPageView
      navbar = new Views.BootstrapNavBarView
        model: HubbyBrand
      window.nbview = navbar
      MSGBUS.events.trigger 'main-navbar:show', navbar
      
    MSGBUS.events.trigger 'mainpage:show', layout


  
  MSGBUS.commands.setHandler 'mainpage:init', () ->
    initialize_page()
    