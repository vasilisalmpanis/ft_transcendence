import * as bootstrap	from 'bootstrap';
import ftReact									from "../ft_react";
import { apiClient }							from "../api/api_client";
import {
	C_PROFILE_HEADER,
	C_PROFILE_USERNAME
}												from "../conf/content_en";
import BarLayout								from "../components/barlayout";
import Alert									from "../components/alert";
import Avatar									from "../components/avatar";
import EditIcon									from "../components/edit_icon";
import ClipboardIcon							from "../components/clipboard_icon";
import StatsLayout								from "../components/statslayout";
import BlockedUsers								from "../components/blocked_users";
import IncomingRequests							from "../components/incoming requests";
import OutgoingRequests							from "../components/outgoing_requests";
import ReRoutePage								from './reroute';

let reroute_number = -1;

const ProfileCard = (props) => {
	const [img, setImg] = ftReact.useState(props.data.avatar);
	const [tfa, setTfa] = ftReact.useState("");
	const [error, setError] = ftReact.useState("");
	const [imgUpdated, setImgUpdated] = ftReact.useState(false);
	const [tfaEnabled, setTfaEnabled] = ftReact.useState(localStorage.getItem('2fa') === 'true');
	const updateMe = async () => {
		if (img && img instanceof Blob) {
			const reader = new FileReader();
    		reader.onload = async function(readerEvent) {
				const base64 = readerEvent.target.result;
				const resp = await apiClient.post("/users/me", {"avatar": base64});
				if (resp.error)
					setError(resp.error);
				else
					localStorage.setItem("me", JSON.stringify(resp));
    		};
			reader.readAsDataURL(img);
		}
	}
	return (
		<div className="justify-content-center" style="width: 18rem;">
			<ul className="list-group list-group-flush">
				<li className="list-group-item">
					<form
						onSubmit={async (event)=>{
							event.preventDefault();
  							const formData = new FormData(event.target);
							const resp = await apiClient.post(
								'/users/me',
								formData,
							)
							if (resp.error)
								setError(resp.error)
							else {
								localStorage.setItem("me", JSON.stringify(resp));
								setImgUpdated(false);
							}
						}}
						className="d-flex flex-column gap-3"
						enctype="multipart/form-data"
						method="post"
					>
						<div>
						<Avatar img={img}/>
						<h5 className="">{props.data.username}</h5>
						<span
							className="btn translate-middle rounded-pill position-absolute badge rounded-circle bg-primary"
							style={{
								overflow: "hidden",
								top: "75%",
								left: "75%",
							}}
						>
							<EditIcon/>
							<input
								style={{
									position: "absolute",
									top: 0,
									right: 0,
									minWidth: "100%",
									minHeight: "100%",
									filter: "alpha(opacity=0)",
									opacity: 0,
									outline: "none",
									cursor: "inherit",
									display: "block",
								}}
								className="input-control"
								type="file"
								name='avatar'
								id="imageInput"
								accept="image/*"
								onChange={(event)=>{
    								if (event.target.files[0]) {
										setImg(event.target.files[0]);
										setImgUpdated(true);
    								}
								}}
							/>
						</span>
						</div>
						<button type="submit" className={imgUpdated ? "btn btn-outline-primary" : "btn btn-outline-primary disabled"}>Save avatar</button>
					</form>
				</li>
				<li className="list-group-item">
					{
						tfaEnabled
							? <button
								className="btn btn-outline-primary w-100"
								onClick={
									async ()=>{
										const res = await apiClient.delete("/2fa");
										if (res.error)
											setError(res.error)
										else
										{
											localStorage.setItem("2fa", false);
											setTfaEnabled(false);
										}
									}
								}
							>
								Disable 2FA
							</button>
							: <button
								data-bs-toggle="modal"
								data-bs-target="#exampleModal"
								className="btn btn-outline-primary w-100"
								onClick={
									async ()=>{
										const res = await apiClient.post("/2fa");
										if (res.error)
											setError(res.error);
										else if (res.secret) {
											setTfa(res.secret);
										}
									}
								}
							>
								Enable 2FA
							</button>
					}
				</li>
				{error && <Alert msg={error}/>}
			</ul>
			<div
				className="modal fade"
				id="exampleModal"
				tabindex="-1"
				aria-labelledby="exampleModalLabel"
				aria-hidden="true"
			>
  				<div class="modal-dialog modal-dialog-centered">
  					<div className="modal-content">
  						<div className="modal-body">
  							<h3
								className="modal-title fs-5 text-break"
								id="exampleModalLabel"
							>
									Add this secret to your authenticator app:
							</h3>
							<button
								type="button"
								className="f-inline-flex align-items-center btn btn-link text-decoration-none"
								onClick={()=>{navigator.clipboard.writeText(tfa)}}
							>
								<span className="me-1 mb-1 text-break">{tfa}</span>
								<ClipboardIcon/>
							</button>
							<form
								onSubmit={async (ev)=>{
									ev.preventDefault();
									const code = ev.target[0].value;
									const res = await apiClient.post("/2fa/verify", {"2fa_code": code});
									if (res.status === '2FA Verified')
									{
										apiClient.authorize(res, null, true);
										setTfaEnabled(true);
										bootstrap.Modal.getInstance('#exampleModal').hide()
										const backdrops = document.getElementsByClassName('modal-backdrop');
										if (backdrops.length) {
											const len = backdrops.length;
											for (let i = 0; i < len; i++) {
												backdrops[0]?.parentNode?.removeChild(backdrops[0]);
											}
										}
										setError(null);
										props.route(`/reroute?path=me`);
									}
									else if (res.error) {
										setError(res.error);
									}
								}}
								className="d-flex flex-row gap-3 my-3"
							>
								<input
									placeholder={"Code from authenticator app"}
									className="form-control"
									type="number"
									max={999999}
									required
								/>
								<button type="submit" className="btn btn-outline-primary">OK</button>
							</form>
							{error && <Alert msg={error}/>}
  						</div>
  					</div>
  				</div>
			</div>
		</div>
	);
}

const Profile = (props) => {
	const me = JSON.parse(localStorage.getItem("me"));
	const [blockedUsers, setBlockedUsers] = ftReact.useState(null);
	const [incomingRequests, setIncomingRequests] = ftReact.useState(null);
	const [outgoingRequests, setOutgoingRequests] = ftReact.useState(null);
	const [stats, setStats] = ftReact.useState(null);
	const [error, setError] = ftReact.useState("");
	if (!me)
		props.route("/signin", {from: {path: "/profile"}});
	ftReact.useEffect(async () => {
		const getMyStats = async () => {
			if (!me) {
				props.route("/signin", {from: {path: "/profile"}});
				return ;
			}
			const data = await apiClient.get(`/users/${me.id}/stats`);
			if (data.error)
				setError(data.error);
			else if (data && !stats)
				setStats(data);
		}
		if (!stats && !error)
			await getMyStats();
	},[stats]);
	ftReact.useEffect(async () => {
		const getBlockedUsers = async () => {
			let data = await apiClient.get(`/block`, {limit: 5, skip: 0});
			if (data.error)
				setError(data.error);
			else if (data && data.length)
				setBlockedUsers([...data]);
		}
		if (!blockedUsers && !error)
			await getBlockedUsers();
	}
	,[blockedUsers]);
	ftReact.useEffect(async () => {
		const getIncomingRequests = async () => {
			const data = await apiClient.get(`/friendrequests/incoming`, {limit: 10, skip: 0});
			if (data.error)
				setError(data.error);
			else if (data && data.length)
				setIncomingRequests([...data]);
		}
		if (!incomingRequests && !error)
			await getIncomingRequests();
	},[incomingRequests]);
	ftReact.useEffect(async () => {
		const getOutgoingRequests = async () => {
			const data = await apiClient.get(`/friendrequests`, {limit: 10, skip: 0});
			if (data.error)
				setError(data.error);
			else if (data && data.length)
				setOutgoingRequests([...data]);
		}
		if (!outgoingRequests && !error)
			await getOutgoingRequests();
	},[outgoingRequests]);
	return (
		<BarLayout route={props.route}>
			{
				me
					?	<div className="d-grid">
							<div className="row border rounded align-items-end text-center mb-3" style={{borderStyle: "solid"}}>
								<div className="col d-flex justify-content-center">
									<ProfileCard data={me} route={props.route}/>
								</div>
								<div className='col d-flex flex-column gap-5 justify-content-between p-2'>
									<div className="col d-flex justify-content-center">
										{stats && <StatsLayout stats={stats}/>}
									</div>
									<form
										className='d-flex flex-column gap-3 justify-content-center px-3'
										style={{minWidth: '8rem'}}
										onSubmit={async (ev)=>{
											ev.preventDefault();
											const username = ev.target[0].value;
											const pass = ev.target[1].value;
											if (!username && !pass) {
												setError("please enter at least something");
												return ;
											}
											let data = {};
											if (username)
												data.username = username;
											if (pass)
												data.password = pass;
											const resp = await apiClient.post('/users/me', data);
											if (resp.error)
												setError(resp.error);
											else {
												localStorage.setItem("me", JSON.stringify(resp));
												props.route("/reroute?path=me");
											}
										}}
									>
										<input
											placeholder='new username'
											className="form-control"
											type='text'
										/>
										<input
											placeholder='new password'
											className="form-control"
											type='password'
										/>
										<button className='btn btn-outline-primary'>Save</button>
									</form>
								</div>
							</div>
							<div className="d-flex flex-wrap justify-content-center mt-2 gap-3 mb-2">
								<div className='card flex-grow-1'>
									<IncomingRequests route={props.route} requests={incomingRequests} setter={setIncomingRequests} sent={false}/>
								</div>
								<div className='card flex-grow-1'>
									<OutgoingRequests route={props.route} requests={outgoingRequests} setter={setOutgoingRequests} sent={true}/>
								</div>
								<div className='card flex-grow-1' style={{overflowX: "auto"}}>
									<BlockedUsers route={props.route} users={blockedUsers} setter={setBlockedUsers}/>
								</div>
							</div>
							{error && <Alert msg={error}/>}
						</div>
					:	<button className="spinner-grow" role="status"></button>
			}
		</BarLayout>
	);
}

export default Profile;