var teamsDiv, activeFareDiv, pastFareDiv, pastFareDivider;

var opMode = "";
const LAB_OP = "lab";
const HOME_OP = "home";
const MATCH_OP = "match";

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
    let type = "Normal";
    switch(fare.modifiers){
        case 1:
            type = "Subsidized"
            break;
        case 2:
            type = "Senior"
            break;
    }
    let element = document.createElement("div");
    element.classList.add("fare");
    element.id = id;
    element.innerHTML = `
    <h3>${fare.id}:</h3>
    <span class="tofrom">${fare.src.x.toFixed(0)},${fare.src.y.toFixed(0)} -> ${fare.dest.x.toFixed(0)},${fare.dest.y.toFixed(0)}</span>
    <span id="fare-${fare.id}-pay" style="padding:0">\$${fare.pay.toFixed(0)} / ${fare.reputation}%</span>
    <span id="fare-${fare.id}-modifier" style="display: none" class="bg-neutral">${type}</span>
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
        setVisibility(document.getElementById(`fare-${id}-modifier`), fare.modifiers != 0);
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
    <div style="grid-area:status;text-align:right" id="team-${team.number}-status"></div>
    <div style="grid-area: buttons;" class="team-buttons">
        ${(opMode == LAB_OP? `<button onclick="removeTeam(${team.number})">Remove Team</button>` : "")} 
    </div>
    `

    teamsDiv.appendChild(element);
    return element;
}

async function updateTeams(){
    const req = await fetch("/dashboard/teams"); // relative URL
    const data = await req.json();

    // Sort teams numerically by team.number
    const sorted = Array.isArray(data)
        ? data.slice().sort((a, b) => Number(a.number) - Number(b.number))
        : [];

    const orderIds = [];

    for (var team of sorted){
        let num = team.number;
        let element = document.getElementById(`team-${num}`);
        if(element == null){
            element = generateTeamElement(team, `team-${num}`)
        }
        orderIds.push(element.id);

        document.getElementById(`team-${team.number}-money`).innerText = `\$${team.money.toFixed(0)}`;
        document.getElementById(`team-${team.number}-reputation`).innerText = `${team.karma}%`;
        document.getElementById(`team-${team.number}-fare`).innerText = team.currentFare;
        document.getElementById(`team-${team.number}-x`).innerText = team.position.x.toFixed(2);
        document.getElementById(`team-${team.number}-y`).innerText = team.position.y.toFixed(2);

        // PRESERVED: last position update timing and color
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

        // PRESERVED: last status ping timing and color
        let status = document.getElementById(`team-${team.number}-status`)
        timeDelta = -getTimeUntil(team.lastStatus) * 1000;

        if(timeDelta > 10000000)
            status.innerHTML = "Not Connected"
        else if (timeDelta > 10000)
            status.innerText = `Last Ping: ${(timeDelta/1000).toFixed(0)}s`;
        else
            status.innerText = `Last Ping: ${timeDelta.toFixed(0)}ms`;

        if(timeDelta > 5000)
            status.style.color = "red";
        else
            status.style.color = "unset";
    }

    // Reorder DOM to match sorted order (preserves existing nodes/content)
    const container = teamsDiv || document.getElementById("teams");
    if (container) {
        const header = container.querySelector(".team.header");
        const frag = document.createDocumentFragment();
        for (const id of orderIds) {
            const node = document.getElementById(id);
            if (node) frag.appendChild(node);
        }
        container.textContent = "";
        if (header) container.appendChild(header);
        container.appendChild(frag);
    }

    // Prune any stale team nodes not in the latest data
    const host = teamsDiv || document.getElementById("teams");
    for (const child of Array.from(host.children)) {
        if (child.id && child.id.startsWith("team-") && !orderIds.includes(child.id)) {
            child.remove();
        }
    }
}


async function refreshMode() {
  const labControls = document.getElementById('lab-team-buttons');
  try {
    const res = await fetch('/match');
    const data = await res.json();
    const mode = String((data && data.mode) || '').toLowerCase();
    if (labControls) labControls.style.display = (mode === 'lab') ? '' : 'none';
  } catch (e) {
    if (labControls) labControls.style.display = 'none';
    console.warn('Failed to fetch /match', e);
  }
}

async function addTeam() {
  const input = document.getElementById('add-team-number');
  if (!input) return;
  const num = parseInt(input.value, 10);
  if (!Number.isInteger(num) || num <= 0) {
    alert('Enter a valid positive team number.');
    return;
  }
  try {
    const res = await fetch(`/Lab/AddTeam/${num}`, { method: 'GET' });
    const text = await res.text();
    if (!res.ok) throw new Error(text || `HTTP ${res.status}`);
    input.value = '';
    await updateTeams(); // repopulate table
  } catch (e) {
    console.error(e);
    alert(`Failed to add team: ${e.message}`);
  }
}

// Ensure initial load populates panes and toggles LAB controls
document.addEventListener('DOMContentLoaded', () => {
  if (typeof updateFares === 'function') updateFares();
  if (typeof updateTeams === 'function') updateTeams();
  if (typeof refreshMode === 'function') {
    refreshMode();
    setInterval(refreshMode, 5000);
  }
});

function configureMatch(){
    fetch("/Lab/ConfigMatch", {
        method: "post",
        headers: new Headers({'content-type': 'application/json'}),
        body: JSON.stringify(
            {
                "number":parseInt(document.getElementById("match-num").value),
                "duration":parseInt(document.getElementById("match-duration").value),
            }
        )
    })
}
function startMatch(){
    fetch("/Lab/StartMatch", {
        method: "post"
    })
}

async function updateMatchInfo(){
    // Use special -2 team auth for the dashboard
    let res = await fetch("/match?auth=-2");
    let data = await res.json();

    opMode = data.mode;
    document.getElementById("title").innerText = `${opMode} Dashboard`;

    if(opMode == LAB_OP){
        // Show add team buttons
        document.getElementById("lab-team-buttons").style.display = "unset"
    }

    if(!data.matchStart){
        document.getElementById("match-status").innerText = `Match ${data.match}, Ready`
    } else {
        if(data.timeRemain < 0)
            document.getElementById("match-status").innerText = `Match ${data.match}, Finished`
        else
            document.getElementById("match-status").innerText = `Match ${data.match}, ${data.timeRemain.toFixed(0)}s`
    }
}

window.onload = () => {
  activeFareDiv = document.getElementById("active-fares");
  pastFareDiv = document.getElementById("past-fares");
  pastFareDivider = document.getElementById("fare-divider");
  teamsDiv = document.getElementById("teams");

  setInterval(() => {
    updateFares();
    updateMatchInfo();
  }, 1000);

  // poll teams once per second (was 100ms)
  setInterval(() => {
    updateTeams();
  }, 1000);

  // initial render
  updateTeams();
  refreshMode();
};

async function removeTeam(teamNumber) {
  try {
    const res = await fetch(`/Lab/RemoveTeam/${teamNumber}`, { method: 'GET' });
    const text = await res.text();
    if (!res.ok) throw new Error(text || `HTTP ${res.status}`);
    await updateTeams();
  } catch (e) {
    console.error(e);
    alert(`Failed to remove team: ${e.message}`);
  }
}