_log=function() {
    console.log.apply(console, arguments);
    _log.last=arguments;
}


App=(function() {
    
    var App=function() {
        $('#inputfile').filestyle({buttonText: 'Upload Input', hideFilenameTextbox: true, width: 120});
        $('#inputfile').change(this.load_text_file.bind(this));
        $('#search-btn').click(this.search.bind(this));        
        $('#download-csv').click(this.download_csv.bind(this));
        $('#table').handsontable({
            colHeaders: ['Query', 'Name', 'Address', 'Phone', 'City', 'Zip', 'State', 'Country', 'Email 1', 'Email 2', 'Website'],
            colWidths: [110, 150, 190, 160, 90, 90, 90, 90, 100, 100, 190],
            data: [['', '', '', '', '', '', '', '', '', '', '']],
        });
        var placeholder='Type in keywords here or upload input file';
        var origin_color=$('#inputtext').css('color');
        var placeholder_color='#bbb';
        $('#inputtext')
            .focus(function() {
                if(this.value==placeholder) {
                    this.value='';
                    $('#inputtext').css('color', origin_color);
                }
            })
            .blur(function() {
                if(this.value=='') {
                     this.value=placeholder;
                     $('#inputtext').css('color', placeholder_color);
                }
            })
            .val(placeholder)
            .css('color', placeholder_color);
    }


    App.prototype.load_text_file=function() {
        var f=new FileReader();
        f.readAsText($('#inputfile').prop('files')[0]);
        f.onload=function(e) {
            $('#inputtext').val(e.target.result);
        };
    }
    

    App.prototype.search=function() {
        $("#indicator").show();
        var params = {
            places: $('#inputtext').val(),
            emails: $('#get-emails').prop('checked'),
        };
        $.post('/search', params).done(this.show_result.bind(this));
    }


    App.prototype.show_result=function(r) {
        var a = r.result;
        if(a.length==0) {
            a.push(['', '', '', '', '', '', '', '', '', '', '']);
        }
        var b=[]; 
        for(var i=0; i<a.length; i++) {
            b.push([a[i].query, a[i].name, a[i].address, a[i].phone, a[i].city, a[i].zip, a[i].state, a[i].country,
                a[i].email1, a[i].email2, a[i].website]);
        }
        var tbl=$('#table').data('handsontable');
        //$('#table').loadData([]);
        tbl.loadData(b);
        $("#indicator").hide();
    }
    

    App.prototype.download_csv=function() {
        var tbl=$('#table').data('handsontable');
        if(!tbl) return;
        var data=tbl.getData();
        if(data.length==0) return;
        s='';
        for(var i=0; i<data.length; i++) {
            for(var j=0; j<data[i].length; j++) {
                s+='"'+data[i][j]+'",';
            }
            s+='\n';
        }
        var b='data:text/csv;base64,'+btoa(s);
        $('<a>').prop('href', b).attr('id', 'x123').attr('download', 'result.csv').appendTo('body');
        document.getElementById('x123').click();
    }
    
    
    App.prototype.toString=function() {
        return '<app object>';
    }
    
    return App;
})();


$(function() {
    app=new App();
});
