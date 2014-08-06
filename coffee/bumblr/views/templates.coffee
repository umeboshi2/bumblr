define (require, exports, module) ->
  $ = require 'jquery'
  _ = require 'underscore'
  Backbone = require 'backbone'
  teacup = require 'teacup'
  marked = require 'marked'
  
  renderable = teacup.renderable

  div = teacup.div
  # I use "icon" for font-awesome
  icon = teacup.i
  strong = teacup.strong
  span = teacup.span
  label = teacup.label
  input = teacup.input

  raw = teacup.raw
  text = teacup.text

  # Main Templates must use teacup.
  # The template must be a teacup.renderable, 
  # and accept a layout model as an argument.

  # Tagnames to be used in the template.
  {div, span, link, text, strong, label, input, 
  button, a, nav, form, small, section, 
  ul, li, b, h1, h2, aside, p,
  header} = teacup
            
  ########################################
  # Templates
  ########################################
                  
  ########################################
  make_menu = renderable (model) ->
    cls = '.' + model.tagclass + '.ctx-menu.nav.navbar.navbar-nav'
    ul cls, ->
      li '.dropdown', ->
        a '.dropdown-toggle', 'data-toggle':'dropdown', ->
          text model.label
          b '.caret'
        ul '.dropdown-menu', ->
          for entry in model.entries
            li ->
              a href:entry.url, entry.name
            

            
  PageLayoutTemplate = renderable () ->
    div '.wrapper', ->
      div '#main-header'
      div '#content-wrapper', ->
        aside '#sidebar'
        section '#main-content'
    div '#footer'

  BootstrapNavBarTemplate = renderable (brand) ->
    div '.container', ->
      div '.navbar-header', ->
        button '.navbar-toggle', type:'button', 'data-toggle':'collapse',
        'data-target':'.navbar-collapse', ->
          span '.sr-only', 'Toggle Navigation'
          span '.icon-bar'
          span '.icon-bar'
          span '.icon-bar'
        a '.navbar-brand', href:brand.url, brand.name
      div '.navbar-collapse.collapse', ->
        ul '.nav.navbar-nav', ->
          li ->
            a href:'#', 'Home'
          li ->
            a href:'#demo', 'Demo'
        ul '.nav.navbar-nav.navbar-ight', ->
          li ->
            a href:'#settings', 'Settings'
              

  BootstrapLayoutTemplate = renderable () ->
    div '#main-navbar.navbar.navbar-default.navbar-fixed-top',
    role:'navigation'
    div '.container-fluid', ->
      div '.row', ->
        div '#sidebar.col-sm-2'
        div '#main-content.col-sm-9'
        
    div '#footer'
    

  main_sidebar = renderable (model) ->
    div '.sidebar-menu', ->
      for entry in model.entries
        div '.sidebar-entry.top-button', ->
          a href:entry.url, entry.name          
  

  consumer_key_form = renderable (settings) ->
    div '.form-group', ->
      label '.control-label', for:'input_key', 'Consumer Key'
      input '#input_key.form-control',
      name:'consumer_key', 'data-validation':'consumer_key',
      placeholder:'', value: settings.consumer_key
    div '.form-group', ->
      label '.control-label', for:'input_secret', 'Consumer Secret'
      input '#input_secret.form-control',
      name:'consumer_secret', 'data-validation':'consumer_secret',
      placeholder:'', value: settings.consumer_secret
    div '.form-group', ->
      label '.control-label', for:'input_token', 'Token'
      input '#input_token.form-control',
      name:'token', 'data-validation':'token',
      placeholder:'', value: settings.token
    div '.form-group', ->
      label '.control-label', for:'input_tsecret', 'Token Secret'
      input '#input_tsecret.form-control',
      name:'token_secret', 'data-validation':'token_secret',
      placeholder:'', value: settings.token_secret
    input '.btn.btn-default.btn-xs', type:'submit', value:'Submit'
    
  module.exports =
    PageLayoutTemplate: PageLayoutTemplate
    BootstrapLayoutTemplate: BootstrapLayoutTemplate
    BootstrapNavBarTemplate: BootstrapNavBarTemplate
    main_sidebar: main_sidebar
    make_menu: make_menu
    consumer_key_form: consumer_key_form
    











