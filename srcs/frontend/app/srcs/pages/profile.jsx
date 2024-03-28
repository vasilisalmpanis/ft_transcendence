import ftReact		from "../ft_react";
import { apiClient } from "../api/api_client";
import BarLayout from "../components/barlayout";
import { C_PROFILE_HEADER, C_PROFILE_USERNAME } from "../conf/content_en";
import Alert from "../components/alert";

const ProfileCard = (props) => {
	return (
		<div className="card" style="width: 18rem;">
			<div className="card-body">
				<h5 className="card-title">{C_PROFILE_HEADER}</h5>
			</div>
			<ul className="list-group list-group-flush">
				<li className="list-group-item">{C_PROFILE_USERNAME}: {props.data.username}</li>
			</ul>
		</div>
	);
}

const Profile = (props) => {
	const [me, setMe] = ftReact.useState(null);
	const [error, setError] = ftReact.useState("");
	const getMe = async () => {
		const data = await apiClient.get("/users/me");
		if (data.error)
			setError(data.error)
		else if (data && !me)
			setMe(data);
	};
	if (!me && !error)
		getMe();
	//ftReact.useEffect(()=>{
	//	if (!me && !error)
	//		getMe();
	//},[]);
	return (
		<BarLayout route={props.route}>
			{
				me
					? <ProfileCard data={me}/>
					: error
						? <Alert msg={error}/>
						: (
							<div className="spinner-grow" role="status">
								<span className="visually-hidden">Loading...</span>
				  			</div>
						)
			}
		</BarLayout>
	);
}

export default Profile;