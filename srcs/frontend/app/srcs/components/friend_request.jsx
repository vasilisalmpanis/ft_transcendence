import ftReact          from "../ft_react";
import { apiClient }    from "../api/api_client";

let reroute_number = -1;

const FriendRequestLayout = (props) => {
	const acceptRequest = async () => {
		const data = await apiClient.post(`/friendrequests/accept`, {request_id: props.request.id});
		if (data.error)
			return ;
		else {
			props.setter([...props.data.filter((request) => request.id !== props.request.id)]);
		}
	};
	const declineRequest = async () => {
		const data = await apiClient.post(`/friendrequests/decline`, {request_id: props.request.id});
		if (data.error)
			return ;
		else {
			props.setter([...props.data.filter((request) => request.id !== props.request.id)]);
		}
	};
	const canceRequest = async () => {
		const data = await apiClient.put(`/friendrequests`, {request_id: props.request.id});
		if (data.error)
			return ;
		else {
			props.setter([...props.data.filter((request) => request.id !== props.request.id)]);
		}
	};
	return (
		<li className="list-group-item">
				{props.sent
				?
				<div className="w-100 d-flex flex-row justify-content-between gap-2">
					<h5 style={{wordWrap: "break-word", maxWidth: "15ch"}}>{props.request.receiver.username}</h5>
					<button className="btn btn-danger" onClick={canceRequest}>Cancel</button>
				</div>				
				:
				<div className="d-flex w-100 flex-row align-items-center justify-content-center gap-2">
					<span className="mr-5" style={{wordWrap: "break-word", maxWidth: "15ch"}}>{props.request.sender.username}</span>
					<button className="btn btn-primary" onClick={acceptRequest}>Accept</button>
					<button className="btn btn-danger" onClick={declineRequest}>Decline</button>
				</div>
			}
		</li>
	)	
}

export default FriendRequestLayout;