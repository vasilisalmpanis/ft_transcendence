import ftReact	from "../ft_react";
import Layout 	from "../components/layout";
import BarLayout from "../components/barlayout";

const Score = (props) => (
	<div style={{
		marginTop: "10px",
		textAlign: "center",
	}}>
		<span id="score-board">{`${props.score.s1} : ${props.score.s1}`}</span>
	</div>
);

const Platform = (props) => {
	const style = {
		width: "10px",
		height: "20%",
		backgroundColor: "royalblue",
		position: "absolute",
		top: `${props.y}%`,
	};
	let id = "pl-left";
	if (props.right) {
		id = "pl-right";
		style.right = "1%";
	} else
		style.left = "1%";
	return (
		<div id={id} style={style}/>
	);
}

const Pong = (props) => {
	let ball = {x: 50, y: 50};
	let score = {s1: 0, s2: 0};
	let pl = 40;
	let pr = 40;
	let ws = null;
	let me = 'left';
	let platformDirection = '';
	const keyPress = (ev) => {
		if (ws && ws.readyState === WebSocket.OPEN) {
			switch (ev.key) {
				case 'ArrowUp':
					ws.send(JSON.stringify({"message": "up", "d": me}));
					platformDirection = "up";
					break;
				case 'ArrowDown':
					ws.send(JSON.stringify({"message": "down", "d": me}));
					platformDirection = "down";
					break;
			}
		}
	};
	const keyRelease = (event) => {
		if (ws && ws.readyState === WebSocket.OPEN) {
			if (event.key === 'ArrowUp' && platformDirection === 'up')
			{
				ws.send(JSON.stringify({"message": "stop", "d": me}));
				platformDirection = '';
			}
			else if (event.key === 'ArrowDown' && platformDirection === 'down')
			{
				ws.send(JSON.stringify({"message": "stop", "d": me}));
				platformDirection = '';
			}
		}
	};
	const cleanup = () => {
		console.log("cleanup");
		document.removeEventListener('keydown', keyPress);
		document.removeEventListener('keyup', keyRelease);
		ws && ws.close();
		ws = null;
	}
	ftReact.useEffect(()=>{
		if (!ws) {
			if (!history.state || !history.state.game_id)
				props.route("/games");
			else
			{
				ws = new WebSocket(
					`ws://${window.location.hostname}:8000/ws`,
					["Authorization", localStorage.getItem("access_token")]
				);
				ws.addEventListener('open', (ev) => {
					ws.send(JSON.stringify({"join": history.state.game_id}));
				});
				ws.addEventListener('message', ev => {
					const data = JSON.parse(ev.data);
					if (
						(data.Problem && data.Problem === 'Connecting to game')
						|| (data.error && data.error === 'Game is full')
					)
						props.route("/games");
					if (data.start)
					{
						console.log(data.start);
						return ;
					}
					if (data.side === 'right')
					{
						me = 'right';
						return ;
					}
					ball.x = data.x;
					ball.y = data.y;
					if ('p1' in data)
						pl = data.p1;
					if ('p2' in data)
						pr = data.p2;
					if ('s1' in data)
						score = {s1: data.s1, s2: data.s2}
				});
				document.addEventListener('keydown', keyPress);
				document.addEventListener('keyup', keyRelease);
			}
		};
		return cleanup;
	},[])
	let pl_dom = null;
	let pr_dom = null;
	let ball_dom = null;
	let score_board = null; 
	const gameLoop = () => {
		if (ball_dom) {
			ball_dom.style.left = `${ball.x - 1}%`;
        	ball_dom.style.top = `${ball.y - 1}%`;
        	pl_dom.style.top = `${pl}%`;
        	pr_dom.style.top = `${pr}%`;
			score_board.textContent = `${score.s1}:${score.s2}`;
		} else {
			pl_dom = document.getElementById("pl-left");
			pr_dom = document.getElementById("pl-right");
			ball_dom = document.getElementById("ball");
			score_board = document.getElementById("score-board");
		}
		requestAnimationFrame(gameLoop);
	}
	requestAnimationFrame(gameLoop);
	return (
		<BarLayout route={props.route}>
			<div style={{
				border: "2px solid rgb(248, 2, 191)",
				borderRadius: "1%",
				boxShadow: "0 0 50px rgba(248, 2, 191, 0.5)",
				padding: 0,
				width: "95%",
				height: "95%",
				position: "relative",
			}}>
				<Score score={score}/>
				<div id="ball" style={{
					height: "2%",
					aspectRatio: "1/1",
					backgroundColor: "rgb(216, 223, 24)",
					borderRadius: "100%",
					position: "absolute",
					left: `${ball.x - 1}%`,
					top: `${ball.y - 1}%`,
				}}/>
				<Platform y={pl}/>
				<Platform right y={pr}/>
			</div>
		</BarLayout>
	);
};

export default Pong;