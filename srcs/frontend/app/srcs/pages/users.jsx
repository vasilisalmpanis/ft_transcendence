import ftReact			from "../ft_react";
import { apiClient }	from "../api/api_client";
import BarLayout 		from "../components/barlayout";
import {
	C_PROFILE_HEADER,
	C_PROFILE_USERNAME
}						from "../conf/content_en";
import Alert from "../components/alert";

const UserCard = (props) => {
	return (
		<div className="card mb-2" style="width: 18rem;">
			<ul className="list-group list-group-flush">
				<li className="list-group-item">{C_PROFILE_USERNAME}: {props.data.name}</li>
			</ul>
		</div>
	);
}

const Users = (props) => {
	const [users, setUsers] = ftReact.useState(null);
	const [error, setError] = ftReact.useState("");
	const getUsers = async () => {
		const data = await apiClient.get("/users");
		if (data.error)
			setError(data.error);
		else if (data && !users)
			setUsers(data);
	};
	if (!users && !error)
		getUsers();
	//ftReact.useEffect(()=>{
	//	getUsers();
	//},[]);
	return (
		<BarLayout route={props.route}>
			{
				users
					? users.map(user => <UserCard data={user}/>)
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

export default Users;