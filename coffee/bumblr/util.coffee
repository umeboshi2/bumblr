define (require, exports, module) ->
  $ = require 'jquery'
  jQuery = require 'jquery'
  _ = require 'underscore'
  
  MSGBUS = require 'msgbus'

  scroll_top_fast = ()  ->
    $('html, body').animate {scrollTop: 0}, 'fast'
    
  
  module.exports =
    scroll_top_fast: scroll_top_fast
    
  
    
