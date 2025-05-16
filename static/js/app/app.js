function alerter(){
    var p = prompt('Please enter Passcode')
    message = "Hello Project User" + p
    alert(message)
}

alerter()

var table = new Tabulator("#project-activity-log", {
    height:"300px", //set the table height option
    rowHeight:40,
    //layout:"fitData",
    persistence:{
        sort:true,
        filter:true,
        columns:true,
      },
      persistenceID:"examplePerststance",
      columns:[
      {title:"Id", field:"id", width:200},
      {title:"Title", field:"title", width:100},
      {title:"Description", field:"description", width:200 }
      
      ],
});
