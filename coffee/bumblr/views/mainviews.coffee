define (require, exports, module) ->
  Backbone = require 'backbone'
  MSGBUS = require 'msgbus'
  Marionette = require 'marionette'

  Templates = require 'views/templates'
  FormViews = require 'views/formviews'
    
  MSGBUS.reqres.setHandler 'mainpage:navbar-color', ->
    navbar = $ '#main-navbar'
    navbar.css 'color'
    
  MSGBUS.reqres.setHandler 'mainpage:navbar-bg-color', ->
    navbar = $ '#main-navbar'
    navbar.css 'background-color'
    

  MSGBUS.reqres.setHandler  
  class MainPageView extends Backbone.Marionette.ItemView
    template: Templates.PageLayoutTemplate

  class MainPageLayout extends Backbone.Marionette.LayoutView
    template: Templates.BootstrapLayoutTemplate
    
  class MainHeaderView extends Backbone.Marionette.ItemView
    template: Templates.main_header
    
  class BootstrapNavBarView extends Backbone.Marionette.ItemView
    template: Templates.BootstrapNavBarTemplate
        
  class ConsumerKeyFormView extends FormViews.FormView
    template: Templates.consumer_key_form
    ui:
      consumer_key: '[name="consumer_key"]'
      consumer_secret: '[name="consumer_secret"]'
      token: '[name="token"]'
      token_secret: '[name="token_secret"]'

    updateModel: ->
      @model.set
        consumer_key: @ui.consumer_key.val()
        consumer_secret: @ui.consumer_secret.val()
        token: @ui.token.val()
        token_secret: @ui.token_secret.val()
        
    createModel: ->
      MSGBUS.reqres.request 'bumblr:get_app_settings'
        
  module.exports =
    MainPageView: MainPageView
    MainPageLayout: MainPageLayout
    MainHeaderView: MainHeaderView
    BootstrapNavBarView: BootstrapNavBarView
    ConsumerKeyFormView: ConsumerKeyFormView
    
  