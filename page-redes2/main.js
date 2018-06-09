$(document).ready(function() {
    $(function(){
        $('.targetDiv').hide();
         $('.active').click(function(){
            $('.targetDiv').hide();
        });

        $('.showSingle').click(function(){
              $('.targetDiv').hide();
              $('#div'+$(this).attr('target')).show();
        });
    });
});
