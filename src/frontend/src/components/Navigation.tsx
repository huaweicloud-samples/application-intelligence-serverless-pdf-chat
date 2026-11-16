import { Link } from "react-router-dom";
import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/solid";

// Static header. User identity is carried by the X-User-Id header;
// APIG App authentication is handled in front of the backend.
const Navigation: React.FC = () => {
  return (
    <nav className="bg-violet-900">
      <div className="container flex flex-wrap items-center justify-between py-3">
        <Link
          to="/"
          className="inline-flex items-center self-center text-2xl font-semibold whitespace-nowrap text-white"
        >
          <ChatBubbleLeftRightIcon className="w-6 h-6 mr-1.5" />
          DocChat
        </Link>
      </div>
    </nav>
  );
};

export default Navigation;
