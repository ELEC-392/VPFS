var teamsDiv, activeFareDiv, pastFareDiv, pastFareDivider;

function setVisibility(element, visible){
    if(!visible)
        element.style.display = "none"
    else
        element.style.display = "unset";
}

function getTimeUntil(utcTimeSeconds){
    let currentTime = (new Date()).getTime() / 1000
    return (utcTimeSeconds - currentTime);
}

function generateFareElement(fare, id){
    let element = document.createElement("div");
    element.classList.add("fare");
    element.id = id;
    element.innerHTML = `
    <h3>${fare.id}:</h3>
    <span class="tofrom">${fare.src.x},${fare.src.y} -> ${fare.dest.x},${fare.dest.y}</span>
    <span id="fare-${fare.id}-pay" style="padding:0">\$${fare.pay.toFixed(0)} / ${fare.reputation}%</span>
    <span id="fare-${fare.id}-claim" style="display: none" class="bg-neutral">Team</span>
    <span id="fare-${fare.id}-pickedUp" style="display:none" class="bg-ok">Picked Up</span>
    <span id="fare-${fare.id}-completed" style="display:none" class="bg-ok">Completed</span>
    <span id="fare-${fare.id}-paid" style="display:none" class="bg-ok">Paid</span>
    <span id="fare-${fare.id}-inPosition" style="display:none" class="bg-warn">In Position</span>
    <span id="fare-${fare.id}-expiry" style="display:none">Expires in </span>
    `

    // if(fare.active)
        activeFareDiv.appendChild(element);
    // else
    //     pastFareDiv.appendChild(element);

    return element;
}

async function updateFares(){
    let req = await fetch("http://localhost:5000/dashboard/fares");
    let data = await req.json();

    for(var fare of data){
        let id = fare.id;
        let element = document.getElementById(`fare-${id}`);
        if(element == null){
            element = generateFareElement(fare, `fare-${id}`)
        }

        // If fare is no longer active, move it
        if(element.parentElement == activeFareDiv && !fare.active){
            if(fare.claimed)
                pastFareDiv.insertBefore(element, pastFareDivider)
            else
                pastFareDiv.insertBefore(element, pastFareDivider.nextSibling);
        }

        team = document.getElementById(`fare-${id}-claim`);
        expiry = document.getElementById(`fare-${id}-expiry`);
        if(fare.claimed){
            team.innerText = `Team ${fare.team}`
            setVisibility(team, true)
            setVisibility(expiry, false)
        }
        else {
            let delta = getTimeUntil(fare.expiry);
            if(delta < 0)
                expiry.innerText = "Expired"
            else
                expiry.innerText = `Expires in ${delta.toFixed(0)}`
            setVisibility(team, false)
            setVisibility(expiry, true)
        }

        setVisibility(document.getElementById(`fare-${id}-inPosition`), fare.inPosition);
        setVisibility(document.getElementById(`fare-${id}-pickedUp`), fare.pickedUp);
        setVisibility(document.getElementById(`fare-${id}-completed`), fare.completed);
        setVisibility(document.getElementById(`fare-${id}-paid`), fare.paid);
    }
}

function generateTeamElement(team, id) {
    let element = document.createElement("div");
    element.classList.add("team");
    element.id = id;
    element.innerHTML = `
    <h3 style="grid-area: title;">Team ${team.number}</h3>
    <div style="grid-area: money;">
        Money: <span id="team-${team.number}-money">${team.money}</span><br/>
        Reputation: <span id="team-${team.number}-reputation">${team.karma}%</span><br/>
        Current Fare: <span id="team-${team.number}-fare">None</span>
    </div>
    <div style="grid-area: position;">
        X <span id="team-${team.number}-x">${team.position.x.toFixed(2)}</span><br/>
        Y <span id="team-${team.number}-y">${team.position.y.toFixed(2)}</span><br/>
        Last Update: <span id="team-${team.number}-postime">${team.lastPosUpdate}</span>
    </div>
    <div style="grid-area: buttons;">
        <button onclick="removeTeam(${team.number})">Remove Team</button>
    </div>
    `

    teamsDiv.appendChild(element);
    return element;
}

async function updateTeams(){
    let req = await fetch("http://localhost:5000/dashboard/teams");
    let data = await req.json();

    for(var team of data){
        let num = team.number;
        let element = document.getElementById(`team-${num}`);
        if(element == null){
            element = generateTeamElement(team, `team-${num}`)
        }

        document.getElementById(`team-${team.number}-money`).innerText = `\$${team.money.toFixed(0)}`;
        document.getElementById(`team-${team.number}-reputation`).innerText = `${team.karma}%`;
        document.getElementById(`team-${team.number}-fare`).innerText = team.currentFare;
        document.getElementById(`team-${team.number}-x`).innerText = team.position.x.toFixed(2);
        document.getElementById(`team-${team.number}-y`).innerText = team.position.y.toFixed(2);

        let posttime = document.getElementById(`team-${team.number}-postime`);
        timeDelta = -getTimeUntil(team.lastPosUpdate) * 1000;

        if(timeDelta > 10000000)
            posttime.innerHTML = "Never"
        else if (timeDelta > 10000)
            posttime.innerText = `${(timeDelta/1000).toFixed(0)}s`;
        else
            posttime.innerText = `${timeDelta.toFixed(0)}ms`;

        if(timeDelta > 5000)
            posttime.style.color = "red";
        else
            posttime.style.color = "unset";
    }
}

function addTeam(){
    let input = document.getElementById("add-team-number");
    fetch(`/Lab/AddTeam/${input.value}`);
}
function removeTeam(team){
    fetch(`/Lab/RemoveTeam/${team}`);
}

window.onload = () => {
    activeFareDiv = document.getElementById("active-fares");
    pastFareDiv = document.getElementById("past-fares");
    pastFareDivider = document.getElementById("fare-divider");
    teamsDiv = document.getElementById("teams");

    setInterval(() => {
        updateFares();
    }, 1000);
    setInterval(() => {
        updateTeams();
    }, 100);
}